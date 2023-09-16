module float_mult (
    input wire clk,
    input wire rst,
    input wire mult_ready,
    input wire mult_accept,
    output reg mult_valid,
    input wire signed [31:0] mult_in_a,
    input wire signed [31:0] mult_in_b,
    output reg signed [31:0] mult_out_0
);

  //localparams
  localparam mult_b1_INIT = 0;
  localparam mult_b1_S0 = 1;
  localparam mult_b1_FINISH = 2;

  //signals: 
  reg         [ 1:0] mult_state;
  wire signed [63:0] ab;
  wire signed [63:0] ab2;
  reg signed  [31:0] a;
  reg signed  [31:0] b;
  //combinations: 
  assign ab  = (a * b);
  assign ab2 = ab >>> 16;

  always @(posedge clk) begin
    if (rst) begin
      a <= 0;
      b <= 0;
      mult_out_0 <= 0;
      mult_state <= mult_b1_INIT;
    end else begin  //if (rst)
      case (mult_state)
        mult_b1_INIT: begin
          mult_valid <= 0;
          if (mult_ready == 1) begin
            a          <= mult_in_a;  /* float.py [15]: def mult(a: int32, b: int32) -> int32: */
            b          <= mult_in_b;  /* float.py [15]: def mult(a: int32, b: int32) -> int32: */
            mult_state <= mult_b1_FINISH;
          end
        end
        mult_b1_FINISH: begin
          mult_valid <= 1;
          if (mult_accept == 1) begin
            mult_state <= mult_b1_INIT;
          end
          /* ab <= (a * b); */  /* float.py [16]: ab: int64 = a * b */
          mult_out_0 <= {ab2[63], ab2[30:0]};  /* float.py [17]: return ab >> PRECISION */
        end
      endcase
    end
  end


endmodule

